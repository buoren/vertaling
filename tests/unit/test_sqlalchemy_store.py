"""Tests for SQLAlchemyStore — uses SQLite in-memory database."""

from __future__ import annotations

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.sqlalchemy import SQLAlchemyStore


@pytest.fixture
def store():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Session = sessionmaker(bind=engine)
    s = SQLAlchemyStore(session_factory=Session, metadata=metadata)
    metadata.create_all(engine)
    return s


def _complete_unit(code="k1", target="nl", text="Hallo"):
    return TranslationUnit(
        code=code,
        source_locale="en",
        target_locale=target,
        source_text="Hello",
        translated_text=text,
        status=TranslationStatus.COMPLETE,
    )


def _pending_unit(code="k1", target="nl"):
    return TranslationUnit(
        code=code,
        source_locale="en",
        target_locale=target,
        source_text="Hello",
    )


class TestSQLAlchemyStoreGet:
    def test_returns_translated_text(self, store):
        store.save(_complete_unit())
        assert store.get("k1", "en", "nl") == "Hallo"

    def test_returns_none_for_missing(self, store):
        assert store.get("missing", "en", "nl") is None

    def test_returns_none_for_pending(self, store):
        store.save(_pending_unit())
        assert store.get("k1", "en", "nl") is None

    def test_returns_none_for_wrong_locale(self, store):
        store.save(_complete_unit(target="nl"))
        assert store.get("k1", "en", "de") is None


class TestSQLAlchemyStoreSave:
    def test_insert_new(self, store):
        store.save(_complete_unit())
        assert store.get("k1", "en", "nl") == "Hallo"

    def test_upsert_existing(self, store):
        store.save(_complete_unit(text="old"))
        store.save(_complete_unit(text="new"))
        assert store.get("k1", "en", "nl") == "new"

    def test_save_with_context(self, store):
        unit = _complete_unit()
        unit.context = "homepage"
        store.save(unit)
        assert store.get("k1", "en", "nl") == "Hallo"

    def test_save_failed_unit(self, store):
        unit = _pending_unit()
        unit.status = TranslationStatus.FAILED
        unit.error = "API error"
        store.save(unit)
        failed = store.get_failed()
        assert len(failed) == 1
        assert failed[0].error == "API error"


class TestSQLAlchemyStorePending:
    def test_get_pending_returns_pending_units(self, store):
        store.save(_pending_unit(code="a", target="nl"))
        store.save(_pending_unit(code="b", target="de"))
        store.save(_complete_unit(code="c", target="nl"))

        pending = store.get_pending(["nl"])
        assert len(pending) == 1
        assert pending[0].code == "a"

    def test_get_pending_filters_by_locale(self, store):
        store.save(_pending_unit(code="a", target="nl"))
        store.save(_pending_unit(code="b", target="de"))

        pending = store.get_pending(["de"])
        assert len(pending) == 1
        assert pending[0].code == "b"

    def test_get_pending_multiple_locales(self, store):
        store.save(_pending_unit(code="a", target="nl"))
        store.save(_pending_unit(code="b", target="de"))

        pending = store.get_pending(["nl", "de"])
        assert len(pending) == 2


class TestSQLAlchemyStoreFailed:
    def test_get_failed_returns_failed_units(self, store):
        unit = _pending_unit()
        unit.status = TranslationStatus.FAILED
        unit.error = "boom"
        store.save(unit)

        failed = store.get_failed()
        assert len(failed) == 1
        assert failed[0].error == "boom"
        assert failed[0].status == TranslationStatus.FAILED

    def test_get_failed_excludes_non_failed(self, store):
        store.save(_pending_unit())
        store.save(_complete_unit(code="k2"))

        failed = store.get_failed()
        assert len(failed) == 0


class TestSQLAlchemyStoreValidation:
    def test_must_provide_table_or_metadata(self):
        with pytest.raises(ValueError, match="Must provide"):
            SQLAlchemyStore(session_factory=lambda: None)

    def test_custom_table(self):
        from sqlalchemy import Column, String, Table, Text

        engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()
        custom = Table(
            "my_translations",
            metadata,
            Column("code", String(256), primary_key=True),
            Column("locale", String(16), primary_key=True),
            Column("source_locale", String(16), nullable=False),
            Column("source_text", Text, nullable=False),
            Column("translated_text", Text, nullable=True),
            Column("status", String(20), nullable=False, default="pending"),
            Column("context", String(256), nullable=True),
            Column("error", Text, nullable=True),
        )
        metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        store = SQLAlchemyStore(session_factory=Session, table=custom)
        store.save(_complete_unit())
        assert store.get("k1", "en", "nl") == "Hallo"
