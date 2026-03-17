"""Tests for TranslationPipeline orchestration logic."""

from __future__ import annotations

import pytest

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.glossaries.memory import InMemoryGlossary
from vertaling.pipeline import TranslationPipeline
from vertaling.stores.memory import InMemoryTranslationStore
from vertaling.translators.echo import EchoTranslator


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


# --- Multi-store tests ---


@pytest.mark.asyncio
async def test_get_checks_preferred_store_first(pipeline_with_readonly_and_writable_stores):
    """Lookup hits the preferred store before trying others."""
    pipe, readonly, writable, _review = pipeline_with_readonly_and_writable_stores
    unit = TranslationUnit(
        code="app.title",
        source_locale="en",
        target_locale="nl",
        source_text="Hello",
        translated_text="Hallo-json",
        status=TranslationStatus.COMPLETE,
    )
    readonly.save(unit)

    result = await pipe.get("app.title", "Hello", target_locale="nl", store="json")
    assert result == "Hallo-json"


@pytest.mark.asyncio
async def test_get_falls_back_to_next_store_on_miss(pipeline_with_readonly_and_writable_stores):
    """When the preferred store misses, other stores are tried in order."""
    pipe, readonly, writable, _review = pipeline_with_readonly_and_writable_stores
    unit = TranslationUnit(
        code="app.title",
        source_locale="en",
        target_locale="nl",
        source_text="Hello",
        translated_text="Hallo-sql",
        status=TranslationStatus.COMPLETE,
    )
    writable.save(unit)

    result = await pipe.get("app.title", "Hello", target_locale="nl", store="json")
    assert result == "Hallo-sql"


@pytest.mark.asyncio
async def test_miss_on_readonly_store_saves_to_review(pipeline_with_readonly_and_writable_stores):
    """New translations targeting a read-only store go to the review store instead."""
    pipe, readonly, writable, review = pipeline_with_readonly_and_writable_stores

    result = await pipe.get("app.new", "Welcome", target_locale="nl", store="json")
    assert result == "Welcome"  # EchoTranslator returns source

    assert readonly.get("app.new", "en", "nl") is None
    assert review.get("app.new", "en", "nl") == "Welcome"


@pytest.mark.asyncio
async def test_miss_on_writable_store_saves_there(pipeline_with_readonly_and_writable_stores):
    """New translations targeting a writable store are saved directly to it."""
    pipe, readonly, writable, review = pipeline_with_readonly_and_writable_stores

    result = await pipe.get("app.new", "Welcome", target_locale="nl", store="sql")
    assert result == "Welcome"
    assert writable.get("app.new", "en", "nl") == "Welcome"
    assert review.get("app.new", "en", "nl") is None


@pytest.mark.asyncio
async def test_source_locale_override_uses_cached_translation(
    pipeline_with_readonly_and_writable_stores,
):
    """Per-call source_locale finds translations keyed by that locale."""
    pipe, readonly, writable, _review = pipeline_with_readonly_and_writable_stores

    unit = TranslationUnit(
        code="app.dutch_thing",
        source_locale="nl",
        target_locale="de",
        source_text="Welkom",
        translated_text="Willkommen",
        status=TranslationStatus.COMPLETE,
    )
    writable.save(unit)

    result = await pipe.get(
        "app.dutch_thing",
        "Welkom",
        target_locale="de",
        source_locale="nl",
        store="sql",
    )
    assert result == "Willkommen"


@pytest.mark.asyncio
async def test_source_locale_override_translates_with_correct_locale(
    pipeline_with_readonly_and_writable_stores,
):
    """On miss, source_locale override is passed through to the translator."""
    pipe, _readonly, writable, _review = pipeline_with_readonly_and_writable_stores

    result = await pipe.get(
        "app.dutch_thing",
        "Welkom",
        target_locale="de",
        source_locale="nl",
        store="sql",
    )
    assert result == "Welkom"
    assert writable.get("app.dutch_thing", "nl", "de") == "Welkom"


def test_single_store_param_still_works():
    """Backward compat: passing store= wraps it as the default store."""
    store = InMemoryTranslationStore()
    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    pipe = TranslationPipeline(backend=EchoTranslator(), config=config, store=store)
    assert pipe.store is store


def test_passing_both_store_and_stores_raises():
    """Ambiguous config: store= and stores= together is rejected."""
    store = InMemoryTranslationStore()
    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    with pytest.raises(ValueError, match="Cannot pass both"):
        TranslationPipeline(
            backend=EchoTranslator(),
            config=config,
            store=store,
            stores={"a": store},
        )


def test_omitting_all_stores_raises():
    """Pipeline requires at least one store."""
    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    with pytest.raises(ValueError, match="Must pass either"):
        TranslationPipeline(backend=EchoTranslator(), config=config)


@pytest.mark.asyncio
async def test_batch_run_translates_pending_from_all_stores(
    pipeline_with_readonly_and_writable_stores,
):
    """run() aggregates pending from every store and routes saves correctly."""
    pipe, readonly, writable, review = pipeline_with_readonly_and_writable_stores

    readonly.save(
        TranslationUnit(
            code="k1",
            source_locale="en",
            target_locale="nl",
            source_text="One",
        )
    )
    writable.save(
        TranslationUnit(
            code="k2",
            source_locale="en",
            target_locale="nl",
            source_text="Two",
        )
    )

    stats = await pipe.run(target_locales=["nl"])
    assert stats.total_units == 2
    assert stats.complete == 2

    # read-only origin → new translation saved to review store
    assert review.get("k1", "en", "nl") == "One"

    # writable origin → saved in place
    assert writable.get("k2", "en", "nl") == "Two"


@pytest.mark.asyncio
async def test_retry_failed_retranslates_across_all_stores(
    pipeline_with_readonly_and_writable_stores,
):
    """retry_failed() picks up failed units from every store."""
    pipe, readonly, writable, review = pipeline_with_readonly_and_writable_stores

    writable.save(
        TranslationUnit(
            code="k1",
            source_locale="en",
            target_locale="nl",
            source_text="Retry",
            status=TranslationStatus.FAILED,
            error="err",
        )
    )

    stats = await pipe.retry_failed()
    assert stats.total_units == 1
    assert stats.complete == 1
    assert writable.get("k1", "en", "nl") == "Retry"


# --- Glossary integration ---


class FakeTranslator:
    """Translator that uppercases source text, simulating a real translator."""

    async def translate_batch(self, units):
        for u in units:
            u.translated_text = u.source_text.upper()
            u.status = TranslationStatus.COMPLETE
        return units

    def max_batch_chars(self):
        return 1_000_000

    def supported_locales(self):
        return set()


@pytest.mark.asyncio
async def test_glossary_enforces_terms_on_get():
    """get() applies glossary post-processing to translated text."""
    glossary = InMemoryGlossary()
    glossary.add_term("BIRD", "vogel", "en", "nl")

    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(
        backend=FakeTranslator(),
        config=config,
        store=store,
        glossary=glossary,
    )

    result = await pipe.get("app.title", "The bird flies", target_locale="nl")
    # FakeTranslator uppercases → "THE BIRD FLIES"
    # Glossary enforces BIRD → vogel (case-insensitive)
    assert result == "THE vogel FLIES"


@pytest.mark.asyncio
async def test_glossary_enforces_terms_on_translate_batch():
    """translate_batch() applies glossary post-processing."""
    glossary = InMemoryGlossary()
    glossary.add_term("HELLO", "hallo", "en", "nl")

    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(
        backend=FakeTranslator(),
        config=config,
        store=store,
        glossary=glossary,
    )

    units = [
        TranslationUnit(
            code="k1", source_locale="en", target_locale="nl", source_text="Hello world"
        ),
    ]
    results = await pipe.translate_batch(units)
    assert results[0].translated_text == "hallo WORLD"


@pytest.mark.asyncio
async def test_glossary_enforces_terms_on_run():
    """run() applies glossary post-processing."""
    glossary = InMemoryGlossary()
    glossary.add_term("MORNING", "ochtend", "en", "nl")

    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    store = InMemoryTranslationStore()
    store.save(
        TranslationUnit(
            code="k1",
            source_locale="en",
            target_locale="nl",
            source_text="Good morning",
        )
    )

    pipe = TranslationPipeline(
        backend=FakeTranslator(),
        config=config,
        store=store,
        glossary=glossary,
    )

    stats = await pipe.run(target_locales=["nl"])
    assert stats.complete == 1
    assert store.get("k1", "en", "nl") == "GOOD ochtend"


@pytest.mark.asyncio
async def test_glossary_with_scopes():
    """Glossary scopes are passed through correctly."""
    glossary = InMemoryGlossary()
    glossary.add_term("BIRD", "vogel", "en", "nl", scope="global")
    glossary.add_term("BIRD", "snoekje", "en", "nl", scope="project")

    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(
        backend=FakeTranslator(),
        config=config,
        store=store,
        glossary=glossary,
        glossary_scopes=["global", "project"],
    )

    result = await pipe.get("app.title", "The bird", target_locale="nl")
    # "project" scope overrides "global" → BIRD → snoekje
    assert result == "THE snoekje"


@pytest.mark.asyncio
async def test_glossary_attaches_terms_to_units():
    """Units get glossary_terms populated before translation."""
    glossary = InMemoryGlossary()
    glossary.add_term("bird", "vogel", "en", "nl")

    captured_terms = []

    class CapturingTranslator:
        async def translate_batch(self, units):
            for u in units:
                captured_terms.append(u.glossary_terms)
                u.translated_text = u.source_text
                u.status = TranslationStatus.COMPLETE
            return units

        def max_batch_chars(self):
            return 1_000_000

        def supported_locales(self):
            return set()

    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(
        backend=CapturingTranslator(),
        config=config,
        store=store,
        glossary=glossary,
    )

    await pipe.get("k1", "A bird", target_locale="nl")
    assert captured_terms == [{"bird": "vogel"}]


@pytest.mark.asyncio
async def test_no_glossary_leaves_terms_none():
    """Without a glossary, glossary_terms stays None."""
    captured_terms = []

    class CapturingTranslator:
        async def translate_batch(self, units):
            for u in units:
                captured_terms.append(u.glossary_terms)
                u.translated_text = u.source_text
                u.status = TranslationStatus.COMPLETE
            return units

        def max_batch_chars(self):
            return 1_000_000

        def supported_locales(self):
            return set()

    config = TranslationConfig(source_locale="en", target_locales=["nl"])
    store = InMemoryTranslationStore()
    pipe = TranslationPipeline(
        backend=CapturingTranslator(),
        config=config,
        store=store,
    )

    await pipe.get("k1", "Hello", target_locale="nl")
    assert captured_terms == [None]
