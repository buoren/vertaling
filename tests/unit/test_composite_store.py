"""Tests for CompositeStore multi-store routing."""

from __future__ import annotations

import pytest

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.composite import CompositeStore
from vertaling.stores.memory import InMemoryTranslationStore


@pytest.fixture
def stores() -> tuple[InMemoryTranslationStore, InMemoryTranslationStore]:
    return InMemoryTranslationStore(), InMemoryTranslationStore()


@pytest.fixture
def review_store() -> InMemoryTranslationStore:
    return InMemoryTranslationStore()


def _complete_unit(code: str, target: str = "nl", text: str = "Hallo") -> TranslationUnit:
    return TranslationUnit(
        code=code,
        source_locale="en",
        target_locale=target,
        source_text="Hello",
        translated_text=text,
        status=TranslationStatus.COMPLETE,
    )


class TestCompositeGet:
    def test_get_from_preferred_store(self, stores):
        s1, s2 = stores
        s1.save(_complete_unit("k1", text="from-s1"))
        s2.save(_complete_unit("k1", text="from-s2"))

        composite = CompositeStore(stores={"a": s1, "b": s2})
        text, found_in = composite.get("k1", "en", "nl", preferred_store="a")
        assert text == "from-s1"
        assert found_in == "a"

    def test_get_fallback_to_other_store(self, stores):
        s1, s2 = stores
        s2.save(_complete_unit("k1", text="from-s2"))

        composite = CompositeStore(stores={"a": s1, "b": s2})
        text, found_in = composite.get("k1", "en", "nl", preferred_store="a")
        assert text == "from-s2"
        assert found_in == "b"

    def test_get_miss_returns_none(self, stores):
        s1, s2 = stores
        composite = CompositeStore(stores={"a": s1, "b": s2})
        text, found_in = composite.get("missing", "en", "nl")
        assert text is None
        assert found_in is None

    def test_get_no_preferred_uses_registration_order(self, stores):
        s1, s2 = stores
        s1.save(_complete_unit("k1", text="first"))
        s2.save(_complete_unit("k1", text="second"))

        composite = CompositeStore(stores={"a": s1, "b": s2})
        text, found_in = composite.get("k1", "en", "nl")
        assert text == "first"
        assert found_in == "a"

    def test_get_unknown_store_raises(self, stores):
        s1, s2 = stores
        composite = CompositeStore(stores={"a": s1, "b": s2})
        with pytest.raises(KeyError, match="Unknown store"):
            composite.get("k1", "en", "nl", preferred_store="nope")


class TestCompositeSave:
    def test_save_to_writable_store(self, stores):
        s1, s2 = stores
        composite = CompositeStore(stores={"a": s1, "b": s2})
        unit = _complete_unit("k1")
        composite.save(unit, store_name="b")
        assert s2.get("k1", "en", "nl") == "Hallo"
        assert s1.get("k1", "en", "nl") is None

    def test_save_to_read_only_redirects_to_review(self, stores, review_store):
        s1, s2 = stores
        composite = CompositeStore(
            stores={"a": s1, "b": s2},
            read_only={"a"},
            review_store=review_store,
        )
        unit = _complete_unit("k1")
        composite.save(unit, store_name="a")
        assert review_store.get("k1", "en", "nl") == "Hallo"
        assert s1.get("k1", "en", "nl") is None

    def test_save_to_read_only_without_review_raises(self, stores):
        s1, s2 = stores
        composite = CompositeStore(
            stores={"a": s1, "b": s2},
            read_only={"a"},
        )
        unit = _complete_unit("k1")
        with pytest.raises(RuntimeError, match="read-only"):
            composite.save(unit, store_name="a")

    def test_save_defaults_to_first_store(self, stores):
        s1, s2 = stores
        composite = CompositeStore(stores={"a": s1, "b": s2})
        unit = _complete_unit("k1")
        composite.save(unit)
        assert s1.get("k1", "en", "nl") == "Hallo"


class TestCompositeAggregation:
    def test_get_pending_aggregates_and_tags(self, stores):
        s1, s2 = stores
        s1.save(TranslationUnit(code="k1", source_locale="en", target_locale="nl", source_text="A"))
        s2.save(TranslationUnit(code="k2", source_locale="en", target_locale="nl", source_text="B"))

        composite = CompositeStore(stores={"a": s1, "b": s2})
        pending = composite.get_pending(["nl"])
        assert len(pending) == 2
        stores_found = {u.store for u in pending}
        assert stores_found == {"a", "b"}

    def test_get_failed_aggregates_and_tags(self, stores):
        s1, s2 = stores
        u1 = TranslationUnit(
            code="k1",
            source_locale="en",
            target_locale="nl",
            source_text="A",
            status=TranslationStatus.FAILED,
            error="err",
        )
        u2 = TranslationUnit(
            code="k2",
            source_locale="en",
            target_locale="nl",
            source_text="B",
            status=TranslationStatus.FAILED,
            error="err",
        )
        s1.save(u1)
        s2.save(u2)

        composite = CompositeStore(stores={"a": s1, "b": s2})
        failed = composite.get_failed()
        assert len(failed) == 2
        stores_found = {u.store for u in failed}
        assert stores_found == {"a", "b"}


class TestCompositeValidation:
    def test_empty_stores_raises(self):
        with pytest.raises(ValueError, match="At least one store"):
            CompositeStore(stores={})
