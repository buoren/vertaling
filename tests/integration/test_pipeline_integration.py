"""Integration tests for the full translation pipeline."""

from __future__ import annotations

import pytest

from vertaling.pipeline import TranslationPipeline


@pytest.mark.asyncio
async def test_full_pipeline_po_and_model_fields(pipeline: TranslationPipeline) -> None:
    """End-to-end: collect from both sources, translate, write back."""
    ...
