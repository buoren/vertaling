"""Tests for Glossary — InMemoryGlossary."""

from __future__ import annotations

from vertaling.glossary.memory import InMemoryGlossary


class TestAddTermAndGetTerms:
    def test_hit(self):
        g = InMemoryGlossary()
        g.add_term("bird", "snoekje", "en", "nl")
        assert g.get_terms("en", "nl") == {"bird": "snoekje"}

    def test_miss_wrong_pair(self):
        g = InMemoryGlossary()
        g.add_term("bird", "snoekje", "en", "nl")
        assert g.get_terms("nl", "en") == {}

    def test_empty_store(self):
        g = InMemoryGlossary()
        assert g.get_terms("en", "nl") == {}

    def test_overwrite_existing_term(self):
        g = InMemoryGlossary()
        g.add_term("bird", "vogel", "en", "nl")
        g.add_term("bird", "snoekje", "en", "nl")
        assert g.get_terms("en", "nl") == {"bird": "snoekje"}


class TestAddEquivalentSet:
    def test_two_locales(self):
        g = InMemoryGlossary()
        g.add_equivalent_set({"en": "bird", "nl": "snoekje"})
        assert g.get_terms("en", "nl") == {"bird": "snoekje"}
        assert g.get_terms("nl", "en") == {"snoekje": "bird"}

    def test_three_locales_all_pairs(self):
        g = InMemoryGlossary()
        g.add_equivalent_set({"en": "bird", "nl": "snoekje", "de": "Vogel"})
        assert g.get_terms("en", "nl") == {"bird": "snoekje"}
        assert g.get_terms("en", "de") == {"bird": "Vogel"}
        assert g.get_terms("nl", "en") == {"snoekje": "bird"}
        assert g.get_terms("nl", "de") == {"snoekje": "Vogel"}
        assert g.get_terms("de", "en") == {"Vogel": "bird"}
        assert g.get_terms("de", "nl") == {"Vogel": "snoekje"}

    def test_multiple_sets_accumulate(self):
        g = InMemoryGlossary()
        g.add_equivalent_set({"en": "bird", "nl": "snoekje"})
        g.add_equivalent_set({"en": "cat", "nl": "kat"})
        terms = g.get_terms("en", "nl")
        assert terms == {"bird": "snoekje", "cat": "kat"}

    def test_get_terms_returns_copy(self):
        g = InMemoryGlossary()
        g.add_equivalent_set({"en": "bird", "nl": "snoekje"})
        result = g.get_terms("en", "nl")
        result["extra"] = "value"
        assert "extra" not in g.get_terms("en", "nl")
