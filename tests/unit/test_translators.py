"""Tests for translators."""

from __future__ import annotations

import pytest

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.translators.echo import EchoTranslator


@pytest.mark.asyncio
async def test_echo_translator_returns_source_text():
    """EchoTranslator sets translated_text to source_text."""
    translator = EchoTranslator()
    units = [
        TranslationUnit(
            code="test.key",
            source_locale="en",
            target_locale="nl",
            source_text="Hello world",
        )
    ]
    results = await translator.translate_batch(units)
    assert len(results) == 1
    assert results[0].translated_text == "Hello world"
    assert results[0].status == TranslationStatus.COMPLETE


def test_echo_translator_max_batch_chars():
    """EchoTranslator accepts very large batches."""
    translator = EchoTranslator()
    assert translator.max_batch_chars() >= 1_000_000


def test_echo_translator_supported_locales():
    """EchoTranslator accepts any locale."""
    translator = EchoTranslator()
    assert translator.supported_locales() == set()
