"""Tests for TranslationPipeline orchestration logic."""

from __future__ import annotations

import pytest

from vertaling.pipeline import TranslationPipeline


@pytest.mark.asyncio
async def test_pipeline_run_with_no_collectors(pipeline: TranslationPipeline) -> None:
    """Pipeline with no registered collectors completes with zero units."""
    ...


@pytest.mark.asyncio
async def test_pipeline_dry_run_does_not_call_backend(pipeline: TranslationPipeline) -> None:
    """Dry run mode does not invoke the backend."""
    ...


@pytest.mark.asyncio
async def test_pipeline_deduplicates_identical_source_text(pipeline: TranslationPipeline) -> None:
    """Identical source_text + target_locale pairs are submitted only once."""
    ...
