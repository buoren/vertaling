"""Tests for TranslationPipeline orchestration logic."""

from __future__ import annotations

import pytest

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.pipeline import TranslationPipeline
from vertaling.stores.memory import InMemoryTranslationStore


@pytest.mark.asyncio
async def test_get_translates_on_miss(pipeline: TranslationPipeline):
    """get() translates via backend when not in store."""
    result = await pipeline.get("app.title", "Hello", target_locale="nl")
    # EchoBackend returns source text
    assert result == "Hello"


@pytest.mark.asyncio
async def test_get_returns_cached(
    pipeline: TranslationPipeline,
    memory_store: InMemoryTranslationStore,
):
    """get() returns cached translation without calling backend."""
    unit = TranslationUnit(
        code="app.title",
        source_locale="en",
        target_locale="nl",
        source_text="Hello",
        translated_text="Hallo",
        status=TranslationStatus.COMPLETE,
    )
    memory_store.save(unit)

    result = await pipeline.get("app.title", "Hello", target_locale="nl")
    assert result == "Hallo"


@pytest.mark.asyncio
async def test_run_with_no_pending(pipeline: TranslationPipeline):
    """Pipeline run with no pending units returns zero stats."""
    stats = await pipeline.run(target_locales=["nl"])
    assert stats.total_units == 0
    assert stats.complete == 0


@pytest.mark.asyncio
async def test_run_translates_pending(
    pipeline: TranslationPipeline,
    memory_store: InMemoryTranslationStore,
):
    """Pipeline run translates pending units from the store."""
    unit = TranslationUnit(
        code="app.greeting",
        source_locale="en",
        target_locale="nl",
        source_text="Good morning",
    )
    memory_store.save(unit)

    stats = await pipeline.run(target_locales=["nl"])
    assert stats.total_units == 1
    assert stats.complete == 1

    # Verify it's now cached
    cached = memory_store.get("app.greeting", "en", "nl")
    assert cached == "Good morning"  # EchoBackend returns source


@pytest.mark.asyncio
async def test_translate_batch_saves_results(
    pipeline: TranslationPipeline,
    memory_store: InMemoryTranslationStore,
):
    """translate_batch() saves results to the store."""
    units = [
        TranslationUnit(
            code="app.a",
            source_locale="en",
            target_locale="nl",
            source_text="One",
        ),
        TranslationUnit(
            code="app.b",
            source_locale="en",
            target_locale="nl",
            source_text="Two",
        ),
    ]
    results = await pipeline.translate_batch(units)
    assert len(results) == 2
    assert all(u.status == TranslationStatus.COMPLETE for u in results)
    assert memory_store.get("app.a", "en", "nl") == "One"
    assert memory_store.get("app.b", "en", "nl") == "Two"


@pytest.mark.asyncio
async def test_get_fallback_disabled_raises(echo_backend):
    """get() raises RuntimeError when fallback_to_source is False and translation fails."""
    from vertaling._core.config import TranslationConfig

    # Create a backend that fails
    class FailBackend:
        async def translate_batch(self, units):
            for u in units:
                u.status = TranslationStatus.FAILED
                u.error = "boom"
            return units

        def max_batch_chars(self):
            return 100_000

        def supported_locales(self):
            return set()

    config = TranslationConfig(
        source_locale="en",
        target_locales=["nl"],
        fallback_to_source=False,
    )
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(backend=FailBackend(), config=config, store=store)

    with pytest.raises(RuntimeError, match="boom"):
        await pipe.get("x", "Hello", target_locale="nl")


@pytest.mark.asyncio
async def test_get_fallback_returns_source_on_failure(echo_backend):
    """get() returns source text when fallback is enabled and translation fails."""
    from vertaling._core.config import TranslationConfig

    class FailBackend:
        async def translate_batch(self, units):
            for u in units:
                u.status = TranslationStatus.FAILED
                u.error = "fail"
            return units

        def max_batch_chars(self):
            return 100_000

        def supported_locales(self):
            return set()

    config = TranslationConfig(
        source_locale="en",
        target_locales=["nl"],
        fallback_to_source=True,
    )
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(backend=FailBackend(), config=config, store=store)

    result = await pipe.get("x", "Hello", target_locale="nl")
    assert result == "Hello"


@pytest.mark.asyncio
async def test_retry_failed(pipeline, memory_store):
    """retry_failed() re-translates failed units."""
    unit = TranslationUnit(
        code="retry.me",
        source_locale="en",
        target_locale="nl",
        source_text="Retry",
        status=TranslationStatus.FAILED,
        error="previous error",
    )
    memory_store.save(unit)

    stats = await pipeline.retry_failed()
    assert stats.total_units == 1
    assert stats.complete == 1
    assert memory_store.get("retry.me", "en", "nl") == "Retry"


@pytest.mark.asyncio
async def test_translate_batch_empty(pipeline):
    """translate_batch with empty list returns empty."""
    results = await pipeline.translate_batch([])
    assert results == []


def test_chunk_respects_limit():
    """_chunk splits units respecting the character limit."""
    units = [
        TranslationUnit(
            code=f"k{i}",
            source_locale="en",
            target_locale="nl",
            source_text="x" * 100,
        )
        for i in range(5)
    ]
    batches = TranslationPipeline._chunk(units, max_chars=250)
    assert len(batches) == 3  # 2+2+1
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1
