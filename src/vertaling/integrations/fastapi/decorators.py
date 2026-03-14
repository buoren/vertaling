"""FastAPI decorators for automatic content translation on endpoints."""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

from vertaling._core.models import TranslationUnit
from vertaling.utilities.codes import make_translation_code

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Field registry
# ---------------------------------------------------------------------------

_field_registry: dict[str, list[str]] = {}


def register_translatable_fields(model_name: str, fields: list[str]) -> None:
    """Register translatable fields for a model.

    Args:
        model_name: Model/table name.
        fields: List of field names that should be translated.
    """
    _field_registry[model_name] = list(fields)


def get_translatable_fields(model_name: str) -> list[str]:
    """Get registered translatable fields for a model.

    Args:
        model_name: Model/table name.

    Returns:
        List of field names.

    Raises:
        KeyError: If the model is not registered.
    """
    return _field_registry[model_name]


# ---------------------------------------------------------------------------
# translate_on_write
# ---------------------------------------------------------------------------


def translate_on_write(
    model_name: str,
    *,
    id_field: str = "id",
    source_locale: str = "en",
    target_locales: list[str] | None = None,
    fields: list[str] | None = None,
) -> Callable[..., Any]:
    """Decorator that translates content after a write endpoint returns.

    After the endpoint executes, extracts translatable fields from the
    response and creates translation units via ``pipeline.translate_batch()``.

    Expects ``pipeline`` in endpoint kwargs (from ``Depends(get_pipeline)``).
    Uses ``BackgroundTasks`` if available in kwargs.

    Args:
        model_name: Model/table name for translation codes.
        id_field: Key in the response dict for the record ID.
        source_locale: Source locale of the content.
        target_locales: Target locales; if None, uses pipeline config.
        fields: Fields to translate; if None, uses registry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            if result is None:
                return result

            pipeline = kwargs.get("pipeline")
            if pipeline is None:
                logger.warning("translate_on_write: no pipeline in kwargs, skipping")
                return result

            field_list = fields or _field_registry.get(model_name, [])
            if not field_list:
                return result

            locales = target_locales or pipeline.config.target_locales
            response = result if isinstance(result, dict) else result

            if isinstance(response, dict):
                record_id = response.get(id_field)
            else:
                record_id = getattr(response, id_field, None)
            if record_id is None:
                return result

            units: list[TranslationUnit] = []
            for field_name in field_list:
                if isinstance(response, dict):
                    source_text = response.get(field_name)
                else:
                    source_text = getattr(response, field_name, None)
                if not isinstance(source_text, str):
                    continue

                code = make_translation_code(model_name, field_name, str(record_id))
                for locale in locales:
                    units.append(
                        TranslationUnit(
                            code=code,
                            source_locale=source_locale,
                            target_locale=locale,
                            source_text=source_text,
                        )
                    )

            if not units:
                return result

            background_tasks = kwargs.get("background_tasks")
            if background_tasks is not None:
                background_tasks.add_task(_run_translate_batch, pipeline, units)
            else:
                await pipeline.translate_batch(units)

            return result

        return wrapper

    return decorator


async def _run_translate_batch(pipeline: Any, units: list[TranslationUnit]) -> None:
    """Helper to run translate_batch, handling both sync and async contexts."""
    try:
        await pipeline.translate_batch(units)
    except Exception:
        logger.exception("Background translation failed")


# ---------------------------------------------------------------------------
# translate_on_read
# ---------------------------------------------------------------------------


def translate_on_read(
    model_name: str,
    *,
    id_field: str = "id",
    source_locale: str = "en",
    fields: list[str] | None = None,
) -> Callable[..., Any]:
    """Decorator that applies translations to a read endpoint's response.

    Before returning, replaces field values with translations from the store
    using ``pipeline.get()`` (translate-on-miss).

    Expects ``pipeline`` and ``locale`` in endpoint kwargs
    (from ``Depends(get_pipeline)`` and ``Depends(get_locale)``).

    No-op when locale equals source_locale.

    Args:
        model_name: Model/table name for translation codes.
        id_field: Key in the response dict for the record ID.
        source_locale: Source locale of the content.
        fields: Fields to translate; if None, uses registry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            if result is None:
                return result

            locale = kwargs.get("locale", source_locale)
            if locale == source_locale:
                return result

            pipeline = kwargs.get("pipeline")
            if pipeline is None:
                logger.warning("translate_on_read: no pipeline in kwargs, skipping")
                return result

            field_list = fields or _field_registry.get(model_name, [])
            if not field_list:
                return result

            if isinstance(result, list):
                for item in result:
                    await _apply_translations(
                        item, model_name, field_list, id_field, locale, source_locale, pipeline
                    )
            else:
                await _apply_translations(
                    result, model_name, field_list, id_field, locale, source_locale, pipeline
                )

            return result

        return wrapper

    return decorator


async def _apply_translations(
    response: Any,
    model_name: str,
    field_list: list[str],
    id_field: str,
    target_locale: str,
    source_locale: str,
    pipeline: Any,
) -> None:
    """Apply translations to a single response item in-place."""
    is_dict = isinstance(response, dict)
    record_id = response.get(id_field) if is_dict else getattr(response, id_field, None)
    if record_id is None:
        return

    for field_name in field_list:
        source_text = response.get(field_name) if is_dict else getattr(response, field_name, None)
        if not isinstance(source_text, str):
            continue

        code = make_translation_code(model_name, field_name, str(record_id))
        translated = await pipeline.get(
            code, source_text, target_locale=target_locale, source_locale=source_locale
        )

        if is_dict:
            response[field_name] = translated
        else:
            setattr(response, field_name, translated)
