"""Tests for FastAPI decorators."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from vertaling.integrations.fastapi.decorators import (
    _field_registry,
    get_translatable_fields,
    register_translatable_fields,
    translate_on_read,
    translate_on_write,
)


@pytest.fixture(autouse=True)
def _clear_registry() -> Any:
    """Clear the field registry before each test."""
    _field_registry.clear()
    yield
    _field_registry.clear()


class TestFieldRegistry:
    def test_register_and_get(self) -> None:
        register_translatable_fields("events", ["name", "description"])
        assert get_translatable_fields("events") == ["name", "description"]

    def test_unknown_model_raises(self) -> None:
        with pytest.raises(KeyError):
            get_translatable_fields("nonexistent")

    def test_overwrite(self) -> None:
        register_translatable_fields("events", ["name"])
        register_translatable_fields("events", ["name", "title"])
        assert get_translatable_fields("events") == ["name", "title"]


class TestTranslateOnWrite:
    @pytest.mark.asyncio()
    async def test_creates_translation_units(self) -> None:
        pipeline = AsyncMock()
        pipeline.config.target_locales = ["nl", "de"]

        @translate_on_write("events", fields=["name"])
        async def create_event(*, pipeline: Any = None) -> dict[str, Any]:
            return {"id": "e1", "name": "Summer Fest"}

        result = await create_event(pipeline=pipeline)
        assert result == {"id": "e1", "name": "Summer Fest"}

        pipeline.translate_batch.assert_called_once()
        units = pipeline.translate_batch.call_args[0][0]
        assert len(units) == 2
        assert units[0].code == "events.name.e1"
        assert units[0].source_text == "Summer Fest"
        assert {u.target_locale for u in units} == {"nl", "de"}

    @pytest.mark.asyncio()
    async def test_uses_background_tasks(self) -> None:
        pipeline = AsyncMock()
        pipeline.config.target_locales = ["nl"]
        background_tasks = MagicMock()

        @translate_on_write("events", fields=["name"])
        async def create_event(
            *,
            pipeline: Any = None,
            background_tasks: Any = None,
        ) -> dict[str, Any]:
            return {"id": "e1", "name": "Fest"}

        await create_event(pipeline=pipeline, background_tasks=background_tasks)
        background_tasks.add_task.assert_called_once()
        pipeline.translate_batch.assert_not_called()

    @pytest.mark.asyncio()
    async def test_preserves_response(self) -> None:
        pipeline = AsyncMock()
        pipeline.config.target_locales = ["nl"]

        @translate_on_write("events", fields=["name"])
        async def create_event(*, pipeline: Any = None) -> dict[str, Any]:
            return {"id": "e1", "name": "Fest", "extra": True}

        result = await create_event(pipeline=pipeline)
        assert result["extra"] is True

    @pytest.mark.asyncio()
    async def test_no_pipeline_skips(self) -> None:
        @translate_on_write("events", fields=["name"])
        async def create_event() -> dict[str, Any]:
            return {"id": "e1", "name": "Fest"}

        result = await create_event()
        assert result == {"id": "e1", "name": "Fest"}

    @pytest.mark.asyncio()
    async def test_uses_registry_fields(self) -> None:
        register_translatable_fields("events", ["name"])
        pipeline = AsyncMock()
        pipeline.config.target_locales = ["nl"]

        @translate_on_write("events")
        async def create_event(*, pipeline: Any = None) -> dict[str, Any]:
            return {"id": "e1", "name": "Fest"}

        await create_event(pipeline=pipeline)
        pipeline.translate_batch.assert_called_once()

    @pytest.mark.asyncio()
    async def test_skips_non_string_fields(self) -> None:
        pipeline = AsyncMock()
        pipeline.config.target_locales = ["nl"]

        @translate_on_write("events", fields=["count"])
        async def create_event(*, pipeline: Any = None) -> dict[str, Any]:
            return {"id": "e1", "count": 42}

        await create_event(pipeline=pipeline)
        pipeline.translate_batch.assert_not_called()

    @pytest.mark.asyncio()
    async def test_none_result(self) -> None:
        pipeline = AsyncMock()

        @translate_on_write("events", fields=["name"])
        async def create_event(*, pipeline: Any = None) -> None:
            return None

        result = await create_event(pipeline=pipeline)
        assert result is None
        pipeline.translate_batch.assert_not_called()


class TestTranslateOnRead:
    @pytest.mark.asyncio()
    async def test_single_dict(self) -> None:
        pipeline = AsyncMock()
        pipeline.get = AsyncMock(return_value="Zomerfest")

        @translate_on_read("events", fields=["name"])
        async def get_event(*, pipeline: Any = None, locale: str = "en") -> dict[str, Any]:
            return {"id": "e1", "name": "Summer Fest"}

        result = await get_event(pipeline=pipeline, locale="nl")
        assert result["name"] == "Zomerfest"

    @pytest.mark.asyncio()
    async def test_list_response(self) -> None:
        pipeline = AsyncMock()
        pipeline.get = AsyncMock(side_effect=["Zomerfest", "Winterfest"])

        @translate_on_read("events", fields=["name"])
        async def list_events(*, pipeline: Any = None, locale: str = "en") -> list[dict[str, Any]]:
            return [
                {"id": "e1", "name": "Summer Fest"},
                {"id": "e2", "name": "Winter Fest"},
            ]

        result = await list_events(pipeline=pipeline, locale="nl")
        assert result[0]["name"] == "Zomerfest"
        assert result[1]["name"] == "Winterfest"

    @pytest.mark.asyncio()
    async def test_noop_for_source_locale(self) -> None:
        pipeline = AsyncMock()

        @translate_on_read("events", fields=["name"])
        async def get_event(*, pipeline: Any = None, locale: str = "en") -> dict[str, Any]:
            return {"id": "e1", "name": "Summer Fest"}

        result = await get_event(pipeline=pipeline, locale="en")
        assert result["name"] == "Summer Fest"
        pipeline.get.assert_not_called()

    @pytest.mark.asyncio()
    async def test_no_pipeline_skips(self) -> None:
        @translate_on_read("events", fields=["name"])
        async def get_event(*, locale: str = "nl") -> dict[str, Any]:
            return {"id": "e1", "name": "Summer Fest"}

        result = await get_event(locale="nl")
        assert result["name"] == "Summer Fest"

    @pytest.mark.asyncio()
    async def test_miss_fallback(self) -> None:
        pipeline = AsyncMock()
        # pipeline.get returns source_text when no translation exists
        pipeline.get = AsyncMock(return_value="Summer Fest")

        @translate_on_read("events", fields=["name"])
        async def get_event(*, pipeline: Any = None, locale: str = "en") -> dict[str, Any]:
            return {"id": "e1", "name": "Summer Fest"}

        result = await get_event(pipeline=pipeline, locale="nl")
        assert result["name"] == "Summer Fest"

    @pytest.mark.asyncio()
    async def test_none_result(self) -> None:
        pipeline = AsyncMock()

        @translate_on_read("events", fields=["name"])
        async def get_event(*, pipeline: Any = None, locale: str = "nl") -> None:
            return None

        result = await get_event(pipeline=pipeline, locale="nl")
        assert result is None
        pipeline.get.assert_not_called()
