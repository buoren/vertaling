"""Tests for GoogleTranslator — mocked, no real API calls."""

from __future__ import annotations

from unittest import mock

import pytest

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.translators.google import GoogleTranslator


@pytest.fixture
def translator():
    t = GoogleTranslator(project_id="test-project")
    # Prevent lazy client init from importing google SDK
    t._client = mock.MagicMock()
    return t


def _unit(code="k1", target="nl", source="en", text="Hello"):
    return TranslationUnit(
        code=code,
        source_locale=source,
        target_locale=target,
        source_text=text,
    )


@pytest.mark.asyncio
async def test_translates_single_unit(translator):
    with mock.patch.object(translator, "_call_google_api", return_value=["Hallo"]) as m:
        units = [_unit()]
        result = await translator.translate_batch(units)

    assert len(result) == 1
    assert result[0].translated_text == "Hallo"
    assert result[0].status == TranslationStatus.COMPLETE
    m.assert_called_once_with(["Hello"], "nl", "en", None)


@pytest.mark.asyncio
async def test_translates_multiple_units_same_locale(translator):
    with mock.patch.object(translator, "_call_google_api", return_value=["Hallo", "Wereld"]):
        units = [_unit(code="k1", text="Hello"), _unit(code="k2", text="World")]
        result = await translator.translate_batch(units)

    assert result[0].translated_text == "Hallo"
    assert result[1].translated_text == "Wereld"


@pytest.mark.asyncio
async def test_groups_by_target_locale(translator):
    calls = []

    def fake_api(texts, target, source, glossary=None):
        calls.append((target, texts))
        return [f"[{target}]{t}" for t in texts]

    with mock.patch.object(translator, "_call_google_api", side_effect=fake_api):
        units = [
            _unit(code="k1", target="nl", text="Hello"),
            _unit(code="k2", target="de", text="World"),
        ]
        result = await translator.translate_batch(units)

    assert len(calls) == 2
    targets = {c[0] for c in calls}
    assert targets == {"nl", "de"}
    assert result[0].status == TranslationStatus.COMPLETE
    assert result[1].status == TranslationStatus.COMPLETE


@pytest.mark.asyncio
async def test_empty_batch_returns_empty(translator):
    result = await translator.translate_batch([])
    assert result == []


@pytest.mark.asyncio
async def test_api_error_marks_units_failed(translator):
    with mock.patch.object(translator, "_call_google_api", side_effect=RuntimeError("API down")):
        units = [_unit(), _unit(code="k2")]
        result = await translator.translate_batch(units)

    assert all(u.status == TranslationStatus.FAILED for u in result)
    assert all("API down" in (u.error or "") for u in result)


@pytest.mark.asyncio
async def test_normalizes_locale_codes_for_api(translator):
    with mock.patch.object(translator, "_call_google_api", return_value=["Hallo"]) as m:
        units = [_unit(source="en-US", target="nl-NL")]
        await translator.translate_batch(units)

    m.assert_called_once_with(["Hello"], "nl", "en", None)


@pytest.mark.asyncio
async def test_preserves_chinese_region_in_api_call(translator):
    with mock.patch.object(translator, "_call_google_api", return_value=["你好"]) as m:
        units = [_unit(source="en", target="zh-TW")]
        await translator.translate_batch(units)

    m.assert_called_once_with(["Hello"], "zh-tw", "en", None)


def test_max_batch_chars():
    t = GoogleTranslator(project_id="test")
    assert t.max_batch_chars() == 30_000


def test_supported_locales_empty():
    t = GoogleTranslator(project_id="test")
    assert t.supported_locales() == set()


# --- Glossary support ---


@pytest.fixture
def glossary_translator():
    t = GoogleTranslator(
        project_id="test-project",
        location="us-central1",
        glossary_id="acro-glossary",
    )
    t._client = mock.MagicMock()
    return t


@pytest.mark.asyncio
async def test_glossary_id_passes_resource_name(glossary_translator):
    with mock.patch.object(glossary_translator, "_call_google_api", return_value=["Hallo"]) as m:
        units = [_unit()]
        await glossary_translator.translate_batch(units)

    m.assert_called_once_with(
        ["Hello"],
        "nl",
        "en",
        "projects/test-project/locations/us-central1/glossaries/acro-glossary",
    )


@pytest.mark.asyncio
async def test_no_glossary_passes_none(translator):
    with mock.patch.object(translator, "_call_google_api", return_value=["Hallo"]) as m:
        units = [_unit()]
        await translator.translate_batch(units)

    m.assert_called_once_with(["Hello"], "nl", "en", None)


def test_glossary_global_location_warns(caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="vertaling.translators.google"):
        GoogleTranslator(project_id="test", location="global", glossary_id="my-glossary")

    assert "glossaries require a regional location" in caplog.text
