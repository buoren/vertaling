"""Integration tests for the full translation pipeline."""

from __future__ import annotations

import pytest

from vertaling._core.models import TranslationUnit
from vertaling.pipeline import TranslationPipeline
from vertaling.stores.memory import InMemoryTranslationStore


@pytest.mark.asyncio
async def test_full_translate_on_miss_flow(
    pipeline: TranslationPipeline,
    memory_store: InMemoryTranslationStore,
):
    """End-to-end: miss -> translate -> cache -> hit."""
    # First call: miss, triggers translation
    result1 = await pipeline.get("page.title", "Welcome", target_locale="nl")
    assert result1 == "Welcome"  # EchoBackend

    # Second call: cache hit
    result2 = await pipeline.get("page.title", "Welcome", target_locale="nl")
    assert result2 == "Welcome"

    # Verify stored
    assert memory_store.get("page.title", "en", "nl") == "Welcome"


@pytest.mark.asyncio
async def test_batch_run_then_get(
    pipeline: TranslationPipeline,
    memory_store: InMemoryTranslationStore,
):
    """Batch run translates pending, then get() returns cached."""
    # Seed pending units
    for code, text in [("a", "Alpha"), ("b", "Beta")]:
        memory_store.save(
            TranslationUnit(
                code=code,
                source_locale="en",
                target_locale="nl",
                source_text=text,
            )
        )

    stats = await pipeline.run(target_locales=["nl"])
    assert stats.total_units == 2
    assert stats.complete == 2

    # Now get() should return cached
    assert await pipeline.get("a", "Alpha", target_locale="nl") == "Alpha"
    assert await pipeline.get("b", "Beta", target_locale="nl") == "Beta"
