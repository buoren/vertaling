"""Background translation task for FastAPI."""

from __future__ import annotations

from typing import Any

from vertaling.pipeline import TranslationPipeline


async def translate_in_background(
    model_instance: Any,
    pipeline: TranslationPipeline,
    fields: list[str] | None = None,
) -> None:
    """Translate a newly created or updated model instance in the background.

    Intended for use with FastAPI's BackgroundTasks. Queues translation of the
    given model instance's translatable fields to all configured target locales.

    Args:
        model_instance: A SQLAlchemy model instance with translatable fields.
        pipeline: The configured TranslationPipeline to use.
        fields: Specific fields to translate; defaults to all translatable fields.

    Usage::

        @app.post("/workshops")
        async def create_workshop(data: WorkshopCreate, background_tasks: BackgroundTasks):
            workshop = Workshop(**data.model_dump())
            db.add(workshop)
            db.commit()
            background_tasks.add_task(
                translate_in_background,
                model_instance=workshop,
                pipeline=translation_pipeline,
            )
    """
    ...
