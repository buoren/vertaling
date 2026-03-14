"""Background translation task for FastAPI."""

from __future__ import annotations

from vertaling._core.models import TranslationUnit
from vertaling.pipeline import TranslationPipeline


async def translate_in_background(
    units: list[TranslationUnit],
    pipeline: TranslationPipeline,
) -> None:
    """Translate a batch of units in the background.

    Intended for use with FastAPI's BackgroundTasks.

    Args:
        units: Translation units to translate.
        pipeline: The configured TranslationPipeline to use.

    Usage::

        @app.post("/content")
        async def create_content(data: ContentCreate, background_tasks: BackgroundTasks):
            units = build_translation_units(data)
            background_tasks.add_task(
                translate_in_background,
                units=units,
                pipeline=pipeline,
            )
    """
    await pipeline.translate_batch(units)
