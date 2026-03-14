"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from vertaling._core.config import TranslationConfig
from vertaling.backends.echo import EchoBackend
from vertaling.pipeline import TranslationPipeline
from vertaling.store.memory import InMemoryPipelineStore


@pytest.fixture
def echo_backend() -> EchoBackend:
    return EchoBackend()


@pytest.fixture
def default_config() -> TranslationConfig:
    return TranslationConfig(
        source_locale="en",
        target_locales=["nl", "de"],
        backend="echo",
    )


@pytest.fixture
def memory_store() -> InMemoryPipelineStore:
    return InMemoryPipelineStore()


@pytest.fixture
def pipeline(
    echo_backend: EchoBackend,
    default_config: TranslationConfig,
    memory_store: InMemoryPipelineStore,
) -> TranslationPipeline:
    return TranslationPipeline(
        backend=echo_backend,
        config=default_config,
        store=memory_store,
    )
