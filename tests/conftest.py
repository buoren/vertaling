"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from vertaling._core.config import TranslationConfig
from vertaling.pipeline import TranslationPipeline
from vertaling.stores.memory import InMemoryTranslationStore
from vertaling.translators.echo import EchoTranslator


@pytest.fixture
def echo_backend() -> EchoTranslator:
    return EchoTranslator()


@pytest.fixture
def default_config() -> TranslationConfig:
    return TranslationConfig(
        source_locale="en",
        target_locales=["nl", "de"],
        backend="echo",
    )


@pytest.fixture
def memory_store() -> InMemoryTranslationStore:
    return InMemoryTranslationStore()


@pytest.fixture
def pipeline(
    echo_backend: EchoTranslator,
    default_config: TranslationConfig,
    memory_store: InMemoryTranslationStore,
) -> TranslationPipeline:
    return TranslationPipeline(
        backend=echo_backend,
        config=default_config,
        store=memory_store,
    )


@pytest.fixture
def pipeline_with_readonly_and_writable_stores(
    echo_backend: EchoTranslator,
    default_config: TranslationConfig,
) -> tuple[
    TranslationPipeline,
    InMemoryTranslationStore,
    InMemoryTranslationStore,
    InMemoryTranslationStore,
]:
    """Pipeline with a read-only store, a writable store, and a review store."""
    readonly_store = InMemoryTranslationStore()
    writable_store = InMemoryTranslationStore()
    review_store = InMemoryTranslationStore()
    pipe = TranslationPipeline(
        backend=echo_backend,
        config=default_config,
        stores={"json": readonly_store, "sql": writable_store},
        read_only=["json"],
        review_store=review_store,
    )
    return pipe, readonly_store, writable_store, review_store
