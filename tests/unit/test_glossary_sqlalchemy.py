"""Tests for SQLAlchemyGlossary — uses SQLite in-memory database."""

from __future__ import annotations

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

from vertaling.glossary.sqlalchemy import SQLAlchemyGlossary


@pytest.fixture
def glossary():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Session = sessionmaker(bind=engine)
    g = SQLAlchemyGlossary(session_factory=Session, metadata=metadata)
    metadata.create_all(engine)
    return g


class TestAddTermAndGetTerms:
    def test_hit(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl")
        assert glossary.get_terms("en", "nl") == {"bird": "snoekje"}

    def test_miss_wrong_pair(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl")
        assert glossary.get_terms("nl", "en") == {}

    def test_empty_glossary(self, glossary):
        assert glossary.get_terms("en", "nl") == {}

    def test_overwrite_existing_term(self, glossary):
        glossary.add_term("bird", "vogel", "en", "nl")
        glossary.add_term("bird", "snoekje", "en", "nl")
        assert glossary.get_terms("en", "nl") == {"bird": "snoekje"}

    def test_multiple_terms_same_pair(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl")
        glossary.add_term("cat", "kat", "en", "nl")
        assert glossary.get_terms("en", "nl") == {"bird": "snoekje", "cat": "kat"}


class TestAddEquivalentSet:
    def test_two_locales(self, glossary):
        glossary.add_equivalent_set({"en": "bird", "nl": "snoekje"})
        assert glossary.get_terms("en", "nl") == {"bird": "snoekje"}
        assert glossary.get_terms("nl", "en") == {"snoekje": "bird"}

    def test_three_locales_all_pairs(self, glossary):
        glossary.add_equivalent_set({"en": "bird", "nl": "snoekje", "de": "Vogel"})
        assert glossary.get_terms("en", "nl") == {"bird": "snoekje"}
        assert glossary.get_terms("en", "de") == {"bird": "Vogel"}
        assert glossary.get_terms("nl", "en") == {"snoekje": "bird"}
        assert glossary.get_terms("nl", "de") == {"snoekje": "Vogel"}
        assert glossary.get_terms("de", "en") == {"Vogel": "bird"}
        assert glossary.get_terms("de", "nl") == {"Vogel": "snoekje"}

    def test_multiple_sets_accumulate(self, glossary):
        glossary.add_equivalent_set({"en": "bird", "nl": "snoekje"})
        glossary.add_equivalent_set({"en": "cat", "nl": "kat"})
        assert glossary.get_terms("en", "nl") == {"bird": "snoekje", "cat": "kat"}


class TestValidation:
    def test_must_provide_table_or_metadata(self):
        with pytest.raises(ValueError, match="Must provide"):
            SQLAlchemyGlossary(session_factory=lambda: None)

    def test_custom_table(self):
        from sqlalchemy import Column, String, Table

        engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()
        custom = Table(
            "my_glossary",
            metadata,
            Column("source_locale", String(16), primary_key=True),
            Column("target_locale", String(16), primary_key=True),
            Column("source_term", String(256), primary_key=True),
            Column("target_term", String(256), nullable=False),
        )
        metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        g = SQLAlchemyGlossary(session_factory=Session, table=custom)
        g.add_term("bird", "snoekje", "en", "nl")
        assert g.get_terms("en", "nl") == {"bird": "snoekje"}
