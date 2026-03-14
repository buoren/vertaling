"""Tests for vertaling utilities."""

from __future__ import annotations

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.memory import InMemoryTranslationStore
from vertaling.utilities.completeness import CompletenessReport, check_completeness
from vertaling.utilities.interpolation import interpolate
from vertaling.utilities.locale import resolve_locale

# --- interpolation ---


def test_interpolate_single_param():
    assert interpolate("+ {count} more", {"count": 3}) == "+ 3 more"


def test_interpolate_multiple_params():
    result = interpolate("Page {current} of {total}", {"current": 1, "total": 5})
    assert result == "Page 1 of 5"


def test_interpolate_unknown_placeholder_left_as_is():
    assert interpolate("Hello {name}", {}) == "Hello {name}"


def test_interpolate_no_placeholders():
    assert interpolate("No params here", {"key": "val"}) == "No params here"


def test_interpolate_float_param():
    assert interpolate("Price: {price}", {"price": 9.99}) == "Price: 9.99"


# --- locale ---


def test_resolve_locale_exact_match():
    assert resolve_locale("nl-NL", ["nl-NL", "en-US"]) == "nl-NL"


def test_resolve_locale_language_only_fallback():
    assert resolve_locale("nl-NL", ["nl", "en", "de"]) == "nl"


def test_resolve_locale_reverse_match():
    assert resolve_locale("nl", ["nl-NL", "en-US"]) == "nl-NL"


def test_resolve_locale_default_fallback():
    assert resolve_locale("fr-FR", ["en", "de"]) == "en"


def test_resolve_locale_custom_default():
    assert resolve_locale("fr-FR", ["en", "de"], default="de") == "de"


# --- completeness ---


def test_check_completeness_all_translated():
    store = InMemoryTranslationStore()
    for code in ["a", "b", "c"]:
        store.save(
            TranslationUnit(
                code=code,
                source_locale="en",
                target_locale="nl",
                source_text=f"text_{code}",
                translated_text=f"vertaling_{code}",
                status=TranslationStatus.COMPLETE,
            )
        )

    reports = check_completeness(store, "en", ["nl"], ["a", "b", "c"])
    assert len(reports) == 1
    assert reports[0].locale == "nl"
    assert reports[0].coverage == 1.0
    assert reports[0].missing_keys == []
    assert reports[0].translated_keys == 3


def test_check_completeness_partial():
    store = InMemoryTranslationStore()
    store.save(
        TranslationUnit(
            code="a",
            source_locale="en",
            target_locale="nl",
            source_text="alpha",
            translated_text="alfa",
            status=TranslationStatus.COMPLETE,
        )
    )

    reports = check_completeness(store, "en", ["nl"], ["a", "b", "c"])
    assert len(reports) == 1
    r = reports[0]
    assert r.translated_keys == 1
    assert r.total_keys == 3
    assert r.missing_keys == ["b", "c"]
    assert abs(r.coverage - 1 / 3) < 0.01


def test_check_completeness_empty_codes():
    store = InMemoryTranslationStore()
    reports = check_completeness(store, "en", ["nl"], [])
    assert reports[0].coverage == 1.0
    assert reports[0].total_keys == 0


def test_check_completeness_multiple_locales():
    store = InMemoryTranslationStore()
    store.save(
        TranslationUnit(
            code="x",
            source_locale="en",
            target_locale="nl",
            source_text="hello",
            translated_text="hallo",
            status=TranslationStatus.COMPLETE,
        )
    )

    reports = check_completeness(store, "en", ["nl", "de"], ["x"])
    assert len(reports) == 2
    assert reports[0].locale == "nl"
    assert reports[0].coverage == 1.0
    assert reports[1].locale == "de"
    assert reports[1].coverage == 0.0
    assert reports[1].missing_keys == ["x"]


def test_completeness_report_coverage_property():
    r = CompletenessReport(locale="nl", total_keys=10, translated_keys=7)
    assert r.coverage == 0.7
