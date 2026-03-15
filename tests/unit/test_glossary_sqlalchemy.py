"""Tests for SQLAlchemyGlossary — uses SQLite in-memory database."""

from __future__ import annotations

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

from vertaling.glossaries.sqlalchemy import SQLAlchemyGlossary


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


class TestScopedTerms:
    def test_scoped_add_and_get(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl", scope="acro")
        assert glossary.get_terms("en", "nl", scopes=["acro"]) == {"bird": "snoekje"}

    def test_scoped_term_not_visible_unscoped(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl", scope="acro")
        assert glossary.get_terms("en", "nl") == {}

    def test_unscoped_term_not_visible_in_scope(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl")
        assert glossary.get_terms("en", "nl", scopes=["acro"]) == {}

    def test_multi_scope_merge_override(self, glossary):
        glossary.add_term("bird", "vogel", "en", "nl", scope="acro")
        glossary.add_term("bird", "snoekje", "en", "nl", scope="acro.dac.xxxx")
        glossary.add_term("cat", "kat", "en", "nl", scope="acro")
        result = glossary.get_terms("en", "nl", scopes=["acro", "acro.dac.xxxx"])
        assert result == {"bird": "snoekje", "cat": "kat"}

    def test_scope_order_matters(self, glossary):
        glossary.add_term("bird", "vogel", "en", "nl", scope="a")
        glossary.add_term("bird", "snoekje", "en", "nl", scope="b")
        assert glossary.get_terms("en", "nl", scopes=["a", "b"]) == {"bird": "snoekje"}
        assert glossary.get_terms("en", "nl", scopes=["b", "a"]) == {"bird": "vogel"}

    def test_equivalent_set_with_scope(self, glossary):
        glossary.add_equivalent_set({"en": "bird", "nl": "snoekje"}, scope="acro")
        assert glossary.get_terms("en", "nl", scopes=["acro"]) == {"bird": "snoekje"}
        assert glossary.get_terms("nl", "en", scopes=["acro"]) == {"snoekje": "bird"}
        assert glossary.get_terms("en", "nl") == {}

    def test_backward_compat_unscoped(self, glossary):
        glossary.add_term("bird", "snoekje", "en", "nl")
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
            Column("scope", String(256), primary_key=True, default=""),
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
