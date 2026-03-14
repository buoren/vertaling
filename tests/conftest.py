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
