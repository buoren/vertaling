"""Tests for FastAPI integration helpers."""

from __future__ import annotations

import pytest

from vertaling._core.models import TranslationUnit
from vertaling.integrations.fastapi.background import translate_in_background
from vertaling.integrations.fastapi.dependencies import get_locale, get_pipeline
from vertaling.pipeline import TranslationPipeline


@pytest.mark.asyncio
async def test_translate_in_background(pipeline: TranslationPipeline):
    """translate_in_background delegates to pipeline.translate_batch."""
    units = [
        TranslationUnit(
            code="bg.test",
            source_locale="en",
            target_locale="nl",
            source_text="Background",
        )
    ]
    await translate_in_background(units, pipeline)
    # Verify it was saved
    result = pipeline.store.get("bg.test", "en", "nl")
    assert result == "Background"


@pytest.mark.asyncio
async def test_get_locale_with_state():
    """get_locale returns locale from request.state."""

    class FakeState:
        locale = "nl"

    class FakeRequest:
        state = FakeState()

    locale = await get_locale(FakeRequest())
    assert locale == "nl"


@pytest.mark.asyncio
async def test_get_locale_fallback():
    """get_locale falls back to 'en' when state is missing."""

    class FakeRequest:
        pass

    locale = await get_locale(FakeRequest())
    assert locale == "en"


def test_get_pipeline_raises_without_override():
    """get_pipeline raises RuntimeError by default."""
    with pytest.raises(RuntimeError, match="get_pipeline"):
        get_pipeline()
